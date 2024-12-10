#!/usr/bin/env python
import os
import sys
import json
import subprocess
import argparse

# Умолчания
OUT = "pods.csv"
NAMESPACE = "ns000000000000000000001"  # Задаём namespace по умолчанию
HEADERS = True
CONSOLE_ONLY = False

# Вывод ошибки и завершение
def error_exit(message):
    print("\nERROR: {0}\n".format(message), file=sys.stderr)
    sys.exit(1)

# Показать справку
def usage():
    print("Usage: {0} [options]".format(sys.argv[0]))
    print("")
    print("Options:")
    print("  -n, --namespace <name>     Specify namespace (default: ns000000000000000000001)")
    print("  -o, --output <file>        Output file (default: pods.csv)")
    print("      --no-headers           Don't include headers in the output")
    print("      --console-only         Output only to console (no file)")
    print("  -h, --help                 Show this help message")
    sys.exit(0)

# Обработка аргументов командной строки
def process_options():
    global NAMESPACE, OUT, HEADERS, CONSOLE_ONLY
    parser = argparse.ArgumentParser(description="Extract Kubernetes pods info.")
    parser.add_argument("-n", "--namespace", default=NAMESPACE, help="Specify namespace")
    parser.add_argument("-o", "--output", default=OUT, help="Output file")
    parser.add_argument("--no-headers", action="store_false", help="Don't include headers in the output")
    parser.add_argument("--console-only", action="store_true", help="Output only to console (no file)")
    parser.add_argument("-h", "--help", action="help", help="Show this help message")
    
    args = parser.parse_args()
    
    NAMESPACE = args.namespace
    OUT = args.output
    HEADERS = args.no_headers
    CONSOLE_ONLY = args.console_only

# Проверка подключения к кластеру
def test_connection():
    try:
        subprocess.check_call(["kubectl", "cluster-info"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        error_exit("Connection to cluster failed. Is kubectl configured correctly?")

# Получение информации о подах
def get_pods():
    # Получаем данные с kubectl
    cmd = ["kubectl", "get", "pods", "--namespace", NAMESPACE, "-o", "json"]
    try:
        data = subprocess.check_output(cmd, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        error_exit("Failed to get pods: {0}".format(e.output))

    # Загружаем данные как JSON
    pods_data = json.loads(data)

    # Если включены заголовки, выводим их
    if HEADERS:
        with open(OUT, 'w') as out_file:
            out_file.write("Namespace,Pod Name,Images,Image IDs,Host IP,Pod IP,Status\n")

    # Обрабатываем данные подов
    pod_lines = []
    for item in pods_data.get("items", []):
        namespace = item["metadata"]["namespace"]
        name = item["metadata"]["name"]
        images = ";".join([container["image"] for container in item["spec"].get("containers", [])])
        image_ids = ";".join([status.get("imageID", "N/A") for status in item["status"].get("containerStatuses", [])])
        host_ip = item["status"].get("hostIP", "N/A")
        pod_ip = item["status"].get("podIP", "N/A")
        phase = item["status"].get("phase", "N/A")
        
        pod_line = "{},{},{},{},{},{},{}".format(namespace, name, images, image_ids, host_ip, pod_ip, phase)
        pod_lines.append(pod_line)

    # Печатаем данные
    if CONSOLE_ONLY:
        print("\n".join(pod_lines))
    else:
        with open(OUT, 'a') as out_file:
            out_file.write("\n".join(pod_lines) + "\n")
        with open(OUT, 'r') as out_file:
            print(out_file.read())

# Основная функция
def main():
    process_options()
    test_connection()
    get_pods()

# Запуск
if __name__ == "__main__":
    main()
