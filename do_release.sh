#!/bin/bash

[ -n "$DEBUG" ] && [[ $(echo "$DEBUG" | tr '[:upper:]' '[:lower:]') =~ ^y|yes|1|on$ ]] && \
        set -xe || set -e


function do_release() {
	echo "Making release"
		
	#find version:
	VERSION=$(grep -e "^_VERSION.*--PKG_VERSION_MARK--.*$" src/nftlist-little.sh | sed 's/\(^_VERSION\s*=\s*\)\(.*\)\(\#.*$\)/\2/' | tr -d '"' | tr -d "'" | xargs)
	
	if [ -z $VERSION ] || ! [[ "$VERSION" =~ ^[a-z|0-9|\.|\-]{3,32}$ ]]; then
		echo "No version has been found, or incorrect version format"
		exit 1
	fi
	
	RELEASE_NAME=nfthelper-$VERSION
	RELEASE_PATH=./release/$RELEASE_NAME.tar.gz

	if [ ! -d "release" ]; then 
		mkdir release
	fi
	
	if [ -f $RELEASE_PATH ]; then 
		echo "File '$RELEASE_PATH' already exists, no thing to do, exiting"
		exit 0
	fi

	#tar --transform "s/^src/$RELEASE_NAME/" -czf $RELEASE_PATH src
	tar --transform "s/^src\/nftlist-little.sh/usr\/local\/bin\/nftlist-little.sh/" \
		--transform "s/^src\/init.d\/nftlist/etc\/init.d\/nftlist/" \
		-czf $RELEASE_PATH src/nftlist-little.sh src/init.d/nftlist
	
	echo "File prepared: $RELEASE_PATH"
}



function do_info() {
  cat << EOF
Usage:
$(basename $0) release
  pack program to .tar.gz archive and place it in ./release direcotry
EOF
}

case "$1" in 
	"release")
		do_release
		;;
	
	"help"|"-h"|"-help"|"--help")
		do_info
		;;
	*)
		do_info
		;;
esac

exit 0
