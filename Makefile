PYTHON ?= python3
PYTHONPATH := src
SYMBOL ?= PaymentService.authorize

.PHONY: demo test knowledge freshness verify check context query wiki-export clean

demo: check context query

test:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m unittest discover -s tests -v
	$(PYTHON) -m unittest discover -s tools/knowledge/tests -v

knowledge:
	$(PYTHON) -m tools.knowledge.build

freshness:
	$(PYTHON) -m tools.knowledge.check_freshness

verify:
	$(PYTHON) -m tools.knowledge.verify

check: test freshness verify

context:
	$(PYTHON) -m tools.knowledge.prepare_context

query:
	$(PYTHON) -m tools.knowledge.query_graph --symbol "$(SYMBOL)" --depth 1

wiki-export:
	$(PYTHON) -m tools.knowledge.export_wiki

clean:
	rm -rf .agent-runtime dist
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
