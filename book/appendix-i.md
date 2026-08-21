<!--
Here is a complete grammar for Lox. The chapters that introduce each part of the
language include the grammar rules there, but this collects them all into one
place.
-->
这里是一份完整的 Lox 文法。引入语言各部分的章节里已经各自给出过文法规则，这里把它们全部收拢到一处。

<!--
-- Syntax Grammar
-->
## 句法文法

<!--
The syntactic grammar is used to parse the linear sequence of tokens into the
nested syntax tree structure. It starts with the first rule that matches an
entire Lox program (or a single REPL entry).
-->
句法文法用来把线性的词法单元序列解析成嵌套的语法树结构。它从第一条能匹配整个 Lox 程序（或一条 REPL 输入）的规则开始。

```ebnf
program        → declaration* EOF ;
```

<!--
-- Declarations
-->
### 声明

<!--
A program is a series of declarations, which are the statements that bind new
identifiers or any of the other statement types.
-->
一个程序是一系列声明——那些绑定新标识符的语句，以及其它任意语句类型。

```ebnf
declaration    → classDecl
               | funDecl
               | varDecl
               | statement ;

classDecl      → "class" IDENTIFIER ( "<" IDENTIFIER )?
                 "{" function* "}" ;
funDecl        → "fun" function ;
varDecl        → "var" IDENTIFIER ( "=" expression )? ";" ;
```

<!--
-- Statements
-->
### 语句

<!--
The remaining statement rules produce side effects, but do not introduce
bindings.
-->
其余的语句规则会产生副作用，但不会引入绑定。

```ebnf
statement      → exprStmt
               | forStmt
               | ifStmt
               | printStmt
               | returnStmt
               | whileStmt
               | block ;

exprStmt       → expression ";" ;
forStmt        → "for" "(" ( varDecl | exprStmt | ";" )
                           expression? ";"
                           expression? ")" statement ;
ifStmt         → "if" "(" expression ")" statement
                 ( "else" statement )? ;
printStmt      → "print" expression ";" ;
returnStmt     → "return" expression? ";" ;
whileStmt      → "while" "(" expression ")" statement ;
block          → "{" declaration* "}" ;
```

<!--
Note that `block` is a statement rule, but is also used as a nonterminal in a
couple of other rules for things like function bodies.
-->
注意 `block` 既是一条语句规则，也在其它几条规则里充当非终结符，比如函数体。

<!--
-- Expressions
-->
### 表达式

<!--
Expressions produce values. Lox has a number of unary and binary operators with
different levels of precedence. Some grammars for languages do not directly
encode the precedence relationships and specify that elsewhere. Here, we use a
separate rule for each precedence level to make it explicit.
-->
表达式产生值。Lox 有若干一元与二元运算符，优先级各不相同。有些语言的文法并不直接编码优先级关系，而是另行说明。这里我们为每个优先级单独写一条规则，好让它一目了然。

```ebnf
expression     → assignment ;

assignment     → ( call "." )? IDENTIFIER "=" assignment
               | logic_or ;

logic_or       → logic_and ( "or" logic_and )* ;
logic_and      → equality ( "and" equality )* ;
equality       → comparison ( ( "!=" | "==" ) comparison )* ;
comparison     → term ( ( ">" | ">=" | "<" | "<=" ) term )* ;
term           → factor ( ( "-" | "+" ) factor )* ;
factor         → unary ( ( "/" | "*" ) unary )* ;

unary          → ( "!" | "-" ) unary | call ;
call           → primary ( "(" arguments? ")" | "." IDENTIFIER )* ;
primary        → "true" | "false" | "nil" | "this"
               | NUMBER | STRING | IDENTIFIER | "(" expression ")"
               | "super" "." IDENTIFIER ;
```

<!--
-- Utility rules
-->
### 辅助规则

<!--
In order to keep the above rules a little cleaner, some of the grammar is
split out into a few reused helper rules.
-->
为了让上面的规则稍稍干净些，文法里有一部分被拆成几条可复用的辅助规则。

```ebnf
function       → IDENTIFIER "(" parameters? ")" block ;
parameters     → IDENTIFIER ( "," IDENTIFIER )* ;
arguments      → expression ( "," expression )* ;
```

<!--
-- Lexical Grammar
-->
## 词法文法

<!--
The lexical grammar is used by the scanner to group characters into tokens.
Where the syntax is [context free][], the lexical grammar is [regular][] -- note
that there are no recursive rules.
-->
词法文法由扫描器用来把字符归组成词法单元。句法是[上下文无关][context free]的，而词法文法则是[正则][regular]的——注意这里没有任何递归规则。

[context free]: https://en.wikipedia.org/wiki/Context-free_grammar
[regular]: https://en.wikipedia.org/wiki/Regular_grammar

```ebnf
NUMBER         → DIGIT+ ( "." DIGIT+ )? ;
STRING         → "\"" <any char except "\"">* "\"" ;
IDENTIFIER     → ALPHA ( ALPHA | DIGIT )* ;
ALPHA          → "a" ... "z" | "A" ... "Z" | "_" ;
DIGIT          → "0" ... "9" ;
```
