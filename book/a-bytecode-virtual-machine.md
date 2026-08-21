# 字节码虚拟机

<!--
Our Java interpreter, jlox, taught us many of the fundamentals of programming
languages, but we still have much to learn. First, if you run any interesting
Lox programs in jlox, you'll discover it's achingly slow. The style of
interpretation it uses -- walking the AST directly -- is good enough for *some*
real-world uses, but leaves a lot to be desired for a general-purpose scripting
language.
-->
我们的 Java 解释器 jlox，已经把程序设计语言的许多基本功教给了我们，但要学的还有很多。首先，若你在 jlox 里跑起任何稍有意思的 Lox 程序，便会发现它慢得令人心疼。它所采用的解释风格——直接遍历 AST——对*某些*现实用途而言已经够用，但对一门通用脚本语言来说，仍有太多不足。

<!--
Also, we implicitly rely on runtime features of the JVM itself. We take for
granted that things like `instanceof` in Java work *somehow*. And we never for a
second worry about memory management because the JVM's garbage collector takes
care of it for us.
-->
此外，我们还隐式地依赖着 JVM 自身的运行时能力。我们想当然地以为，Java 里的 `instanceof` 之类的东西总会*以某种方式*工作。我们也从未为内存管理操心过一秒——因为 JVM 的垃圾收集器替我们包办了一切。

<!--
When we were focused on high-level concepts, it was fine to gloss over those.
But now that we know our way around an interpreter, it's time to dig down to
those lower layers and build our own virtual machine from scratch using nothing
more than the C standard library...
-->
当我们还专注于高层概念时，把这些一笔带过并无不妥。但如今我们已经摸熟了解释器的门道，是时候向下掘进到那些更底层的地方，只用 C 标准库，从零动手打造属于我们自己的虚拟机了……
