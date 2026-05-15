@echo off
REM =====================================================
REM  seo-keyword-collector GitHub 上传脚本
REM  使用方法：双击运行，或在 PowerShell 中执行
REM =====================================================

cd /d f:\DevStream-Python\projects\seo-keyword-collector

echo [1/6] 初始化独立 Git 仓库...
git init

echo [2/6] 设置默认分支为 main...
git branch -M main

echo [3/6] 添加所有文件到暂存区...
git add .

echo [4/6] 创建首次提交...
git commit -m "feat: initial commit - Industrial B2B SEO Keyword Collector"

echo.
echo ======================================================
echo  请在 https://github.com/new 创建仓库后，
echo  将下面命令中的 YOUR_USERNAME 替换为你的 GitHub 用户名，
echo  然后手动在 PowerShell 中执行：
echo.
echo  git remote add origin https://github.com/YOUR_USERNAME/seo-keyword-collector.git
echo  git push -u origin main
echo ======================================================
echo.
pause
