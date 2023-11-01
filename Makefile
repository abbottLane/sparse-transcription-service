venv: venv/touchfile alloenv/touchfile

venv/touchfile: requirements.txt
	test -d venv || virtualenv -p python3.8 venv
	. venv/bin/activate; pip install --upgrade pip
	. venv/bin/activate; pip install -Ur requirements.txt
	touch venv/touchfile

alloenv/touchfile: requirements.txt
	test -d alloenv || virtualenv -p python3.7 alloenv
	. alloenv/bin/activate; pip install -Ur app/agents/media_processing/requirements.txt
	. alloenv/bin/activate; mkdir alloenv/lib/python3.7/site-packages/allosaurus/pretrained/
	. alloenv/bin/activate; cp -R app/agents/media_processing/kunwinjku_allosaurus/wlane120920 alloenv/lib/python3.7/site-packages/allosaurus/pretrained
	touch alloenv/touchfile

install: venv

test: venv
	. venv/bin/activate; py.test tests

clean:
	rm -rf venv
	rm -rf alloenv
	find -iname "*.pyc" -delete

run-dev: install
	. venv/bin/activate; uvicorn  app.main:sparzan --reload --env-file uvienv.conf

run: install
	. venv/bin/activate; uvicorn app.main:sparzan --env-file uvienv.conf

init-db:
	. venv/bin/activate; python init_database.py