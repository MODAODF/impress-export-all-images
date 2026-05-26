#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

PRJNAME = impress-export-all-images
VERNUM = `cat VERSION`
LANGS = en_US zh_TW

FILES = \
    Addons.xcu \
    META-INF/manifest.xml \
    description.xml \
    pkg-desc/pkg-description.en \
    pkg-desc/pkg-description.zh-tw \
    icons/ \
    pythonpath/ \
    main.py \
    README.md \
    VERSION

all: $(FILES) mo
	$(shell ./update_version.sh)
	zip -r $(PRJNAME)-$(VERNUM).oxt $(FILES) VERSION locales

pot:
	pygettext3 --output-dir locales -o $(PRJNAME).pot \
	    pythonpath/exportimages.py pythonpath/i18n.py

mo:
	for lang in $(LANGS); do \
	    msgfmt locales/$$lang/$(PRJNAME).po \
	        -o locales/$$lang/LC_MESSAGES/$(PRJNAME).mo; \
	done

clean:
	rm -f $(PRJNAME)-*.oxt
	find locales -name '*.mo' -delete
