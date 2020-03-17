package main

import "fmt"

func addOptimize(uuid string, repo string, recordID string) {
	element := JudgePoolElement{
		Uuid:       uuid,
		Repo:       repo,
		Success:    make([]string, 0),
		Fail:       make([]string, 0),
		Pending:    make([]string, 0),
		Running:    make([]string, 0),
		RunningSet: make(map[string]bool),
		Total:      0,
		RecordID:   recordID,
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
		element.Pending = append(element.Pending, id)
	}
	optimizePool = append(optimizePool, element)
}

func addCodegen(uuid string, repo string, recordID string) {
	element := JudgePoolElement{
		Uuid:       uuid,
		Repo:       repo,
		Success:    make([]string, 0),
		Fail:       make([]string, 0),
		Pending:    make([]string, 0),
		Running:    make([]string, 0),
		RunningSet: make(map[string]bool),
		Total:      0,
		RecordID:   recordID,
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
		element.Pending = append(element.Pending, id)
	}
	codegenPool = append(codegenPool, element)
}
