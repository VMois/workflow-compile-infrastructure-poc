# Workflow Compile Infrastructure PoC

PoC to create a library that will take different workflow languages (like CWL) 
and compile them to an Intermediate Representation (IR)
that can be executed by a different engines (Kubernetes, AWS EC2, etc.).
Idea is very similar to how LLVM works.

This repository is used only to test the idea of converting workflows in different languages
to a common representation.

**NOT FOR PRODUCTION USE** 

## IR format details

IR represented as a **graph**.
Node properties:

| key         | value    | notes  |
|-------------|----------|--------|
| id          | *string* | unique id within the IR graph | 
| type        | *string* | can be `task` or `io` (can be replaced with *int* to save space) | 
| metadata    | *object* | metadata related  |
| data        | *object* | diff data is stored depending on a node type |
