#
# Makefile
#

none:

install:
	if test "${INSTALL_DIR}" = ""; then echo "error: INSTALL_DIR not defined"; exit 1; fi
	if test -e ${INSTALL_DIR}; then rm -rf ${INSTALL_DIR}; fi
	:
	mkdir -p ${INSTALL_DIR}
	mkdir -p ${INSTALL_DIR}/usr/bin
	:
	(cd static; tar cf - etc/*) | (cd ${INSTALL_DIR}; tar xvf -)
	(cd static; tar cf - usr/bin/*) | (cd ${INSTALL_DIR}; tar xvf -)
	(cd static; tar cf - usr/lib/hcron/*) | (cd ${INSTALL_DIR}; tar xvf -)
	(cd static; tar cf - usr/sbin/*) | (cd ${INSTALL_DIR}; tar xvf -)
	(cd static; tar cf - usr/share/*) | (cd ${INSTALL_DIR}; tar xvf -)
	#(cd static; tar cf - var/*) | (cd ${INSTALL_DIR}; tar xvf -)
