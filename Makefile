update_python:
	# Without --upgrade uv will reuse the already pinnend version from the requirements.txt.
	# https://docs.astral.sh/uv/pip/compile/#upgrading-requirements
	uv pip compile pyproject.toml -o requirements.txt --upgrade
