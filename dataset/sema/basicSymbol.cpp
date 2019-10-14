/*
Test Package: Sema_Local_Preview
Test Target: Basic Symbols
Author: Pikachu
Time: 2019-10-14
*/

int _a; // expected error: _ cannot be the first symbol of identifier
int 123; // expected error: numbers cannot be the first symbol of identifier
// =============================
int a;
int a; // expected error: redefinition of variable a
// =============================
//int[] a[10]; // This is an undefined behavior, which means it won't be tested in the online test but you can have a try
void b; // expected error: variable cannot be void type
// Notice that the following code is syntax correct in cpp
// But we define this as undefined behavior
// int b = 0;
// class b{
//      int b = 0;
// };
int int; // expected error: type identifier cannot be variable identifier
int bool; // expected error: type identifier cannot be variable identifier
bool class; // expected error: reserved word cannot be variable identifier
void functionF(){} // accepted
