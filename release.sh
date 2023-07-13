#!/bin/bash

set -e

# Cheap way of getting the version specified in addon.xml
# Credit: https://stackoverflow.com/a/45058060/944717
VERSION=v`grep -oP '<addon.*version="\K\d+\.\d+\.\d+' addon.xml`

# We have to 'target' our PR against a known release (and branch)
# of the repo-scripts repository. Define that here.
TARGET_RELEASE=matrix

CHANGELOG_FOR_VERSION=`sed '1,/^'$VERSION'$/d' changelog.txt`

# Tag the branch with the extracted version.
git tag $VERSION
git push origin $VERSION

# push the files to github.
gh release create $VERSION --generate-notes

# Specify depth to speed up clone.
git clone git@github.com:xbmc/repo-scripts.git --branch $TARGET_RELEASE --depth 1
cd repo-scripts
git remote add me git@github.com:powlo/repo-scripts.git


git checkout -b weather.metoffice@$TARGET_RELEASE

# Pull the same tarball we released moments ago. This ensures that the same files are
# used in the repo-scripts release as the github release.
curl -L https://github.com/powlo/weather.metoffice/archive/refs/tags/$VERSION.tar.gz | tar -xz
cp -r weather.metoffice-*/* weather.metoffice
git add weather.metoffice/
git commit -m "[weather.metoffice] $VERSION"
git push me

envsubst < ../pr_template.txt > pr_body.txt
gh pr create \
    --title "[weather.metoffice] $VERSION" \
    --body-file pr_body.txt \
    --repo xbmc/repo-scripts \
    --base $TARGET_RELEASE \
    --draft

cd ..
rm -rf repo-scripts