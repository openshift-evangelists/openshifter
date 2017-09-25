build:
	docker build -t docker.io/osevg/openshifter .

release: build
	docker push docker.io/osevg/openshifter
