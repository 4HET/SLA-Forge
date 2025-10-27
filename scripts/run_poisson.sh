#!/usr/bin/env bash
# 泊松到达负载测试脚本
python project/serving/runner.py --traffic configs/traffic.yaml --mode poisson
