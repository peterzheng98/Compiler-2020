/*
Test Package: Sema_Local_Preview
Test Target: Basic
Author: 16' Zihao Xu
Time: 2019-11-11
Verdict: Success
Origin Package: Semantic Pretest
*/
int a = 0;

class A{
    int f(){
       b = a; 
    }
    int b;
};


int main(){
    int[  ][  ] graph = new int[3][];    //be careful about the space!
    graph[0] = null;
    graph[1] = new int[10];
    graph[2] = new int[30];
    
    int i = 0;
    for ((i == 1)&& true;;){
        break;
    }
    return 0;
}

//This is a comment without "\n" at the end of the sentence, may cause a little problem if you don't handle it well.