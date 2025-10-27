#!/usr/bin/env bash
# 突发流量负载测试脚本
python project/serving/runner.py --traffic configs/traffic.yaml --mode bursty
