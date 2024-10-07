
# Set library name here
MODULE ?= default
DLL = $(MODULE).dll

OBJ_DIR = win64
SHELL := sh.exe

# Set tools here
CC = gcc
AR = ar

# Files specification
CFLAGS = -pedantic -DBUILD_DLL -c -ansi -std=c99 -m64 -I.
LDFLAGS = -lm -m64

VPATH := .
SRCS := $(foreach dir, $(VPATH), $(wildcard $(dir)/*.c))
OBJS := $(addprefix $(OBJ_DIR)/, $(notdir $(SRCS:.c=.o)))

.PHONY: all

# Main rules
all: $(DLL)


$(DLL): $(OBJS) $(MODULE).def
	$(CC) -mwindows -mwin32 -shared -static-libgcc $^ $(LDFLAGS) -o $@


clean::
	del $(DLL)
	rmdir /s /q $(OBJ_DIR)


# Rules for C files compilation
$(OBJ_DIR)/%.o: %.c
	-@mkdir $(OBJ_DIR) 2> nul ||:
	$(CC) -c $(CFLAGS) $< -o $@
