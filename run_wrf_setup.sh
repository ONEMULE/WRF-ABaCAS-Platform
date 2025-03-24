#!/bin/bash
# WRF环境设置脚本 - 封装启动器

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BOLD}WRF环境设置脚本${NC}"
echo "这个脚本将启动统一版WRF环境设置工具"

# 检查Python环境
echo -e "\n${GREEN}==> 检查Python环境${NC}"
python3 --version
if [ $? -ne 0 ]; then
    echo -e "${RED}错误: 找不到Python 3，请安装Python 3.6或更高版本${NC}"
    exit 1
fi

# 运行Python设置脚本
echo -e "\n${GREEN}==> 运行统一版Python设置脚本${NC}"
python3 wrf_setup.py --auto-install

# 检查脚本运行结果
if [ $? -ne 0 ]; then
    echo -e "\n${RED}设置脚本报告了错误。请解决上述问题后重试。${NC}"
    exit 1
fi

echo -e "\n${BOLD}设置流程已完成!${NC}"
echo "如需更多选项，请直接运行: python3 wrf_setup.py --help"
echo "现在您可以运行应用: python3 run.py"