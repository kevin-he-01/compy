CC := gcc

SOURCES := $(wildcard *.c)
OBJECTS := $(patsubst %.c,%.o,$(SOURCES))
DEPENDS := $(patsubst %.c,%.d,$(SOURCES))

ERROR := -Werror=all -Werror=incompatible-pointer-types -Werror=int-conversion -Wno-error=unused-parameter
WARNING := -Wall -Wextra -Wformat=2 -Wconversion -Wduplicated-cond -Wlogical-op -Wshift-overflow=2 -Wshadow $(ERROR)

CFLAGS ?= -g

TARGET = runtime.o

.PHONY: all clean

all: $(TARGET)

clean:
	$(RM) $(OBJECTS) $(DEPENDS) $(TARGET)

# Combine object files into one
$(TARGET): $(OBJECTS)
	$(LD) -relocatable $^ -o $@

-include $(DEPENDS)

%.o: %.c Makefile
	$(CC) $(WARNING) $(CFLAGS) -MMD -MP -c $< -o $@

# Adapted from https://stackoverflow.com/a/52036564
# CC BY-SA 4.0
