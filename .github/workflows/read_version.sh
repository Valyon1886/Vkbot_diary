PACKAGE_VERSION=$(python3 ../../VkBotDiary.py -v)

echo ::set-output name=SOURCE_TAG::$PACKAGE_VERSION