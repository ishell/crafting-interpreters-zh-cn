<!--
For your edification, here is the code produced by [the little script
we built][generator] to automate generating the syntax tree classes for jlox.
-->
供你参考，下面是我们为 jlox 自动生成语法树类而写的[那个小脚本][generator]所产出的代码。

[generator]: representing-code.html#metaprogramming-the-trees

<!--
-- Expressions
-->
## 表达式

<!--
Expressions are the first syntax tree nodes we see, introduced in "[Representing
Code](representing-code.html)". The main Expr class defines the visitor
interface used to dispatch against the specific expression types, and contains
the other expression subclasses as nested classes.
-->
表达式是我们见到的第一批语法树节点，在「[表示代码](representing-code.html)」一章引入。主类 `Expr` 定义了用来按具体表达式类型分派的访问者接口，并把其它表达式子类作为嵌套类收在里面。

^code expr

<!--
-- Assign expression
-->
### 赋值表达式

<!--
Variable assignment is introduced in "[Statements and
State](statements-and-state.html#assignment)".
-->
变量赋值在「[语句与状态](statements-and-state.html#assignment)」一章引入。

^code expr-assign

<!--
-- Binary expression
-->
### 二元表达式

<!--
Binary operators are introduced in "[Representing
Code](representing-code.html)".
-->
二元运算符在「[表示代码](representing-code.html)」一章引入。

^code expr-binary

<!--
-- Call expression
-->
### 调用表达式

<!--
Function call expressions are introduced in
"[Functions](functions.html#function-calls)".
-->
函数调用表达式在「[函数](functions.html#function-calls)」一章引入。

^code expr-call

<!--
-- Get expression
-->
### 取值表达式

<!--
Property access, or "get" expressions are introduced in
"[Classes](classes.html#properties-on-instances)".
-->
属性访问，也就是 “get” 表达式，在「[类](classes.html#properties-on-instances)」一章引入。

^code expr-get

<!--
-- Grouping expression
-->
### 分组表达式

<!--
Using parentheses to group expressions is introduced in "[Representing
Code](representing-code.html)".
-->
用括号给表达式分组，在「[表示代码](representing-code.html)」一章引入。

^code expr-grouping

<!--
-- Literal expression
-->
### 字面量表达式

<!--
Literal value expressions are introduced in "[Representing
Code](representing-code.html)".
-->
字面量值表达式在「[表示代码](representing-code.html)」一章引入。

^code expr-literal

<!--
-- Logical expression
-->
### 逻辑表达式

<!--
The logical `and` and `or` operators are introduced in "[Control
Flow](control-flow.html#logical-operators)".
-->
逻辑运算符 `and` 与 `or` 在「[控制流](control-flow.html#logical-operators)」一章引入。

^code expr-logical

<!--
-- Set expression
-->
### 置值表达式

<!--
Property assignment, or "set" expressions are introduced in
"[Classes](classes.html#properties-on-instances)".
-->
属性赋值，也就是 “set” 表达式，在「[类](classes.html#properties-on-instances)」一章引入。

^code expr-set

<!--
-- Super expression
-->
### Super 表达式

<!--
The `super` expression is introduced in
"[Inheritance](inheritance.html#calling-superclass-methods)".
-->
`super` 表达式在「[继承](inheritance.html#calling-superclass-methods)」一章引入。

^code expr-super

<!--
-- This expression
-->
### This 表达式

<!--
The `this` expression is introduced in "[Classes](classes.html#this)".
-->
`this` 表达式在「[类](classes.html#this)」一章引入。

^code expr-this

<!--
-- Unary expression
-->
### 一元表达式

<!--
Unary operators are introduced in "[Representing Code](representing-code.html)".
-->
一元运算符在「[表示代码](representing-code.html)」一章引入。

^code expr-unary

<!--
-- Variable expression
-->
### 变量表达式

<!--
Variable access expressions are introduced in "[Statements and
State](statements-and-state.html#variable-syntax)".
-->
变量访问表达式在「[语句与状态](statements-and-state.html#variable-syntax)」一章引入。

^code expr-variable

<!--
-- Statements
-->
## 语句

<!--
Statements form a second hierarchy of syntax tree nodes independent of
expressions. We add the first couple of them in "[Statements and
State](statements-and-state.html)".
-->
语句构成独立于表达式的第二套语法树节点层级。我们在「[语句与状态](statements-and-state.html)」里先加入其中前几种。

^code stmt

<!--
-- Block statement
-->
### 块语句

<!--
The curly-braced block statement that defines a local scope is introduced in
"[Statements and State](statements-and-state.html#block-syntax-and-semantics)".
-->
用花括号界定局部作用域的块语句，在「[语句与状态](statements-and-state.html#block-syntax-and-semantics)」一章引入。

^code stmt-block

<!--
-- Class statement
-->
### 类语句

<!--
Class declaration is introduced in, unsurprisingly,
"[Classes](classes.html#class-declarations)".
-->
类声明——不出所料——在「[类](classes.html#class-declarations)」一章引入。

^code stmt-class

<!--
-- Expression statement
-->
### 表达式语句

<!--
The expression statement is introduced in "[Statements and
State](statements-and-state.html#statements)".
-->
表达式语句在「[语句与状态](statements-and-state.html#statements)」一章引入。

^code stmt-expression

<!--
-- Function statement
-->
### 函数语句

<!--
Function declarations are introduced in, you guessed it,
"[Functions](functions.html#function-declarations)".
-->
函数声明——你猜对了——在「[函数](functions.html#function-declarations)」一章引入。

^code stmt-function

<!--
-- If statement
-->
### If 语句

<!--
The `if` statement is introduced in "[Control
Flow](control-flow.html#conditional-execution)".
-->
`if` 语句在「[控制流](control-flow.html#conditional-execution)」一章引入。

^code stmt-if

<!--
-- Print statement
-->
### Print 语句

<!--
The `print` statement is introduced in "[Statements and
State](statements-and-state.html#statements)".
-->
`print` 语句在「[语句与状态](statements-and-state.html#statements)」一章引入。

^code stmt-print

<!--
-- Return statement
-->
### Return 语句

<!--
You need a function to return from, so `return` statements are introduced in
"[Functions](functions.html#return-statements)".
-->
要有函数才能从中返回，所以 `return` 语句在「[函数](functions.html#return-statements)」一章引入。

^code stmt-return

<!--
-- Variable statement
-->
### 变量语句

<!--
Variable declarations are introduced in "[Statements and
State](statements-and-state.html#variable-syntax)".
-->
变量声明在「[语句与状态](statements-and-state.html#variable-syntax)」一章引入。

^code stmt-var

<!--
-- While statement
-->
### While 语句

<!--
The `while` statement is introduced in "[Control
Flow](control-flow.html#while-loops)".
-->
`while` 语句在「[控制流](control-flow.html#while-loops)」一章引入。

^code stmt-while
