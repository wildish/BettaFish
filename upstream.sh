#!/bin/bash

set -e

echo "============================"
echo "  Upstream Tag Sync Tool"
echo "============================"

# 确认 upstream 已存在
if ! git remote | grep -q "^upstream$"; then
    echo "❌ 未找到 upstream remote，请先执行："
    echo "    git remote add upstream <repo-url>"
    exit 1
fi

# 1. Fetch upstream
echo "🔄 正在从 upstream 获取 tags..."
git fetch upstream --tags

echo ""
echo "📌 可用的 upstream tags："
echo "---------------------------------"
git tag -l | sort -V
echo "---------------------------------"

# 输入 tag 名称
read -p "请输入你要同步的 tag（如 v2.0.0）: " TAG

# 检查 tag 是否存在
if ! git tag -l | grep -q "^$TAG$"; then
    echo "❌ Tag $TAG 不存在，请重新运行脚本。"
    exit 1
fi

# 设置基线分支名称
BASE_BRANCH="upstream-$TAG"

echo ""
echo "📌 将要创建基线分支：$BASE_BRANCH"
read -p "确认创建吗？ [y/N]: " CONFIRM
if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
    echo "❌ 操作取消。"
    exit 0
fi

# 检查是否已有同名分支
if git branch --list | grep -q "$BASE_BRANCH"; then
    echo "⚠ 本地已存在分支 $BASE_BRANCH"
    read -p "是否删除并重新创建该分支？ [y/N]: " CONFIRM_DEL
    if [[ "$CONFIRM_DEL" != "y" && "$CONFIRM_DEL" != "Y" ]]; then
        echo "❌ 操作取消。"
        exit 0
    fi
    git branch -D "$BASE_BRANCH"
fi

# 2. 创建基线分支
echo "🔧 正在创建基线分支 $BASE_BRANCH..."
git checkout -b "$BASE_BRANCH" "tags/$TAG"

echo "✅ 基线分支创建完成：$BASE_BRANCH"
echo ""

# 3. 选择要 rebase 的本地分支
echo "📌 当前本地分支列表："
git branch
echo "---------------------------------"

read -p "请输入要 rebase 的本地分支名称（如 dev）: " LOCAL_BRANCH

# 检查本地分支是否存在
if ! git branch --list | grep -q " $LOCAL_BRANCH$"; then
    echo "❌ 本地分支 $LOCAL_BRANCH 不存在。"
    exit 1
fi

# 检查是否有未提交修改
if ! git diff-index --quiet HEAD --; then
    echo "⚠ 你有未提交的更改，请先 commit 或 stash！"
    exit 1
fi

# 最终确认
echo ""
echo "⚠⚠⚠ 最终确认 ⚠⚠⚠"
echo "你将执行："
echo "    git checkout $LOCAL_BRANCH"
echo "    git rebase $BASE_BRANCH -X theirs"
echo ""
read -p "是否继续？ [y/N]: " FINAL_CONFIRM
if [[ "$FINAL_CONFIRM" != "y" && "$FINAL_CONFIRM" != "Y" ]]; then
    echo "❌ 操作取消。"
    exit 0
fi

# 4. 执行 rebase
git checkout "$LOCAL_BRANCH"
git rebase "$BASE_BRANCH" -X theirs || {
    echo "⚠ 出现冲突，请手动处理后执行："
    echo "    git rebase --continue"
    exit 1
}

echo ""
echo "🎉 同步完成！"
echo "本地分支 $LOCAL_BRANCH 已 rebase 到 $BASE_BRANCH"
echo "-------------------------------------------"
