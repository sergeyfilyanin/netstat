#!/bin/bash

# Умолчания
OUT="pods.csv"
NAMESPACE="--all-namespaces"
HEADERS=true
CONSOLE_ONLY=false

# Вывод ошибки и завершение
errorExit() {
    echo -e "\nERROR: $1\n" >&2
    exit 1
}

# Показать справку
usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -n, --namespace <name>     Specify namespace (default: all namespaces)"
    echo "  -o, --output <file>        Output file (default: pods.csv)"
    echo "      --no-headers           Don't include headers in the output"
    echo "      --console-only         Output only to console (no file)"
    echo "  -h, --help                 Show this help message"
    exit 0
}

# Обработка аргументов командной строки
processOptions() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -n|--namespace)
                NAMESPACE="--namespace $2"
                shift 2
                ;;
            -o|--output)
                OUT="$2"
                shift 2
                ;;
            --no-headers)
                HEADERS=false
                shift
                ;;
            --console-only)
                CONSOLE_ONLY=true
                OUT="/dev/null"
                shift
                ;;
            -h|--help)
                usage
                ;;
            *)
                usage
                ;;
        esac
    done
}

# Проверка подключения к кластеру
testConnection() {
    kubectl cluster-info >/dev/null 2>&1 || errorExit "Connection to cluster failed. Is kubectl configured correctly?"
}

# Получение информации о подах
getPods() {
    local data

    # Получаем данные с kubectl и обрабатываем их с jq
    data=$(kubectl get pods ${NAMESPACE} -o json | jq -r '
        .items[] | 
        .metadata.namespace + "," + 
        .metadata.name + "," + 
        (.spec.containers | map(.image) | join(";")) + "," + 
        (.status.containerStatuses | map(.imageID // "N/A") | join(";")) + "," + 
        (.status.hostIP // "N/A") + "," + 
        (.status.podIP // "N/A") + "," + 
        .status.phase
    ')

    # Если включены заголовки, выводим их
    if [ "${HEADERS}" == true ]; then
        echo "Namespace,Pod Name,Images,Image IDs,Host IP,Pod IP,Status" > "${OUT}"
    fi

    # Печатаем данные
    if [ "${CONSOLE_ONLY}" == true ]; then
        echo "${data}"
    else
        echo "${data}" >> "${OUT}"
        cat "${OUT}"
    fi
}

# Основная функция
main() {
    processOptions "$@"
    testConnection
    getPods
}

# Запуск
main "$@"
