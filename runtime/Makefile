CC := gcc

SOURCES := $(wildcard *.c)
OBJECTS := $(patsubst %.c,%.o,$(SOURCES))
DEPENDS := $(patsubst %.c,%.d,$(SOURCES))

WARNING := -Wall -Wextra -Wformat=2 -Wconversion -Wduplicated-cond -Wlogical-op -Wshift-overflow=2 -Wshadow

TARGET = main.o
# TARGET = runtime.o

.PHONY: all clean

all: $(TARGET)

clean:
	$(RM) $(OBJECTS) $(DEPENDS) $(TARGET)

# TODO: Combine object files into one
# $(TARGET): $(OBJECTS)
# 	$(LD) -relocatable $^ -o $@

# -include $(DEPENDS)

%.o: %.c Makefile
	$(CC) $(WARNING) $(CFLAGS) -MMD -MP -c $< -o $@
