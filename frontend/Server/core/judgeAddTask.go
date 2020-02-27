package main

import "fmt"

func addOptimize(uuid string, repo string) {
	element := JudgePoolElement{
		uuid:    uuid,
		repo:    repo,
		success: make([]string, 0),
		fail:    make([]string, 0),
		pending: make([]string, 0),
		running: make([]string, 0),
		runningSet:make(map[string]bool),
		total:   0,
	}
	result, err := executionQuery("SELECT optim_uid FROM dataset_optimize")
	if result == nil {
		fmt.Printf("runtime error: result is null")
		return
	}
	defer result.Close()

	for result.Next() {
		var id string
		err = result.Scan(&id)
		if err != nil {
			fmt.Printf("runtime warning:%s when scanning the optimize database", err.Error())
		}
		element.pending = append(element.pending, id)
	}
	optimizePool = append(optimizePool, element)
}

func addCodegen(uuid string, repo string) {
	element := JudgePoolElement{
		uuid:    uuid,
		repo:    repo,
		success: make([]string, 0),
		fail:    make([]string, 0),
		pending: make([]string, 0),
		running: make([]string, 0),
		runningSet:make(map[string]bool),
		total:   0,
	}
	result, err := executionQuery("SELECT cg_uid FROM dataset_codegen")
	if result == nil {
		fmt.Printf("runtime error: result is null\n")
		return
	}
	defer result.Close()

	for result.Next() {
		var id string
		err = result.Scan(&id)
		if err != nil {
			fmt.Printf("runtime warning:%s when scanning the codegen database", err.Error())
		}
		element.pending = append(element.pending, id)
	}
	codegenPool = append(codegenPool, element)
}
