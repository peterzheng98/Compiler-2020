package main

import (
	"database/sql"
	"fmt"
)

func executionQuery(cmd string) (*sql.Rows, error) {
	// Execute the query
	//logger(fmt.Sprintf("SQL Query: %s", cmd), 1)
	result, err := db.Query(cmd)
	if err != nil {
		logger(fmt.Sprintf("SQL Runtime error: %s", err.Error()), 0)
		return nil, err
	}
	if result == nil {
		logger(fmt.Sprintf("SQL Runtime error: Execution with return empty cursor"), 0)
		return nil, fmt.Errorf("execution with return empty cursor")
	}
	return result, err
}

func executionExec(cmd string) (sql.Result, error) {
	//logger(fmt.Sprintf("SQL Execution: %s", cmd), 1)
	result, err := db.Exec(cmd)
	if err != nil {
		logger(fmt.Sprintf("SQL Runtime error: %s", err.Error()), 0)
		return nil, err
	}
	return result, err
}

