// zips everything!

find . -maxdepth 1 -type d ! -name '.' | while read dir; do
    dirname=$(basename "$dir")
    zip -r -9 "${dirname}.zip" "$dirname"
done
