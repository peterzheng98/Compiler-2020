/*
Test Package: Sema_Local_Preview
Test Target: Break and Continue
Author: 10' Youer Pu
Time: 2019-10-20
Verdict: Fail
Comment: break outside the loop
Origin Package: Semantic Pretest
*/

int main() {
    while (1) { }
    break;
    return 0;
}
