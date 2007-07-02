#!/bin/sh
if [ $# -lt 2 ]; then
    echo "Usage: api_migration_kit.sh sourceroot updateapi.data.sed"
    echo "This kit should be run in order to update customized installation of"
    echo "CDS Invenio, to reflect current updates to name of functions."
    exit 1
fi

echo -n "Migrating apis..."
# Running sed against all the wmls and pys
find $1 \( -name "*.py" -or -name "*.wml" \) -exec sed -i.bak -f $2 '{}' +
echo " Ok!"

# Pruning non modified .bak files
echo "These files were changed and suitable backup files were created:"
for file in `find $1 -name "*.bak"`; do
    diff --brief $file `dirname $file`/`basename $file .bak`  > /dev/null
    if [ $? -eq 0 ]; then
        rm -f $file
    else
        echo `dirname $file`/`basename $file .bak`
    fi
done

