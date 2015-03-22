
all:
	javac -d $(shell pwd) FixedLBJChunker.java

test:
	echo 'Alice has a cat .' | java -cp $$CLASSPATH:$(shell pwd) FixedLBJChunker

clean:
	rm -f FixedLBJChunker*.class *~
