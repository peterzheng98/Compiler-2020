package main

type sendFormat struct {
	Code    int               `json:"code"`
	Message map[string]string `json:"message"`
}

type sendFormatWeb struct {
	Code    int                 `json:"code"`
	Message map[string][]string `json:"message"`
}

type sendFormatList struct {
	Code    int        `json:"code"`
	Message [][]string `json:"message"`
}

type simpleSendFormat struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
}

type userLoginFormat struct {
	StuID       string `json:"stu_id"`
	StuPassword string `json:"stu_password"`
}

type userAddFormat struct {
	StuId       string `json:"stu_id"`
	StuRepo     string `json:"stu_repo"`
	StuName     string `json:"stu_name"`
	StuPassword string `json:"stu_password"`
	StuEmail    string `json:"stu_email"`
}

type dataSemanticFormat struct {
	SourceCode  string  `json:"source_code"`
	Assertion   bool    `json:"assertion"`
	TimeLimit   float32 `json:"time_limit, omitempty"`
	InstLimit   int     `json:"inst_limit, omitempty"`
	MemoryLimit int     `json:"memory_limit, omitempty"`
	Testcase    string  `json:"testcase"`
}

type dataCodegenFormat struct {
	SourceCode    string  `json:"source_code"`
	Assertion     bool    `json:"assertion"`
	TimeLimit     float32 `json:"time_limit, omitempty"`
	InstLimit     int     `json:"inst_limit, omitempty"`
	MemoryLimit   int     `json:"memory_limit, omitempty"`
	InputContext  string  `json:"input_context"`
	OutputContext string  `json:"output_context"`
	OutputCode    int     `json:"output_code"`
	BasicType     int     `json:"basic_type"`
}

type subtaskSemanticFormat struct {
	Uuid            string  `json:"uuid"`
	Repo            string  `json:"repo"`
	TestCase        string  `json:"testCase"`
	Stage           int     `json:"stage"`
	Subworkid       string  `json:"subWorkId"`
	InputSourceCode string  `json:"inputSourceCode"`
	Assertion       string  `json:"assertion"`
	TimeLimit       float32 `json:"timeLimit"`
	MemoryLimit     int     `json:"memoryLimit"`
	TaskID          string  `json:"taskID"`
	TestCaseID      string  `json:"test_case_id"`
}

type subtaskCodegenFormat struct {
	Uuid            string  `json:"uuid"`
	Repo            string  `json:"repo"`
	TestCase        string  `json:"testCase"`
	Stage           int     `json:"stage"`
	Subworkid       string  `json:"subWorkId"`
	InputSourceCode string  `json:"inputSourceCode"`
	InputContent    string  `json:"inputContent"`
	OutputCode      int     `json:"outputCode"`
	OutputContent   string  `json:"outputContent"`
	TimeLimit       float32 `json:"timeLimit"`
	MemoryLimit     int     `json:"memoryLimit"`
	TaskID          string  `json:"taskID"`
	TestCaseID      string  `json:"test_case_id"`
}

type requestCodegenTaskFormat struct {
	Code   int                    `json:"code"`
	Target []subtaskCodegenFormat `json:"target"`
	WorkID string                 `json:"workid"`
}

type requestSemanticTaskFormat struct {
	Code   int                     `json:"code"`
	Target []subtaskSemanticFormat `json:"target"`
	WorkID string                  `json:"workid"`
}

type requestJudgeFormat struct {
	Uuid string `json:"uuid"`
	Repo string `json:"repo"`
}

type submitTaskElement struct {
	SubworkId   string   `json:"subWorkId"`
	JudgeResult []string `json:"JudgeResult"`
	Judger      string   `json:"Judger"`
	JudgeTime   string   `json:"JudgeTime"`
	TestCase    string   `json:"testCase"`
	Judgetype   int      `json:"judgetype"`
	Uuid        string   `json:"uuid"`
	GitHash     string   `json:"git_hash"`
	TaskID      string   `json:"taskID"`
	TestcaseID  string   `json:"test_case_id"`
}

type JudgePoolElement struct {
	Uuid       string          `json:"uuid"`
	Repo       string          `json:"repo"`
	Githash    string          `json:"githash"`
	RecordID   string          `json:"record_id"`
	Build      bool            `json:"build"`
	Success    []string        `json:"success"`
	Fail       []string        `json:"fail"`
	Pending    []string        `json:"pending"`
	Running    []string        `json:"running"`
	RunningSet map[string]bool `json:"running_set"`
	Total      int             `json:"total"`
}

type submitBuiltTaskElement struct {
	Ident        string `json:"ident"`
	Repo         string `json:"repo"`
	RecordID     string `json:"recordID"`
	UUID         string `json:"uuid"`
	Verdict      string `json:"verdict"`
	GitHash      string `json:"gitHash"`
	GitCommit    string `json:"gitCommit"`
	BuildMessage string `json:"message"`
}
