; ModuleID = "module"
target triple = "x86_64-apple-darwin21.6.0"
target datalayout = "e-m:o-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"

declare i32 @"printf"(i8* %".1", ...)

define i32 @"sum"(i32 %".1")
{
entry:
  %".3" = icmp eq i32 %".1", 1
  br i1 %".3", label %"entry.if", label %"entry.else"
entry.if:
  ret i32 %".1"
entry.else:
  %".6" = sub i32 %".1", 1
  %".7" = call i32 @"sum"(i32 %".6")
  %".8" = add i32 %".1", %".7"
  ret i32 %".8"
entry.endif:
  ret i32 0
}

define i32 @"main"()
{
main_entry:
  %".2" = call i32 @"sum"(i32 5)
  %".3" = getelementptr [3 x i8], [3 x i8]* @"format_string", i32 0, i32 0
  %".4" = call i32 (i8*, ...) @"printf"(i8* %".3", i32 %".2")
  ret i32 0
}

@"format_string" = internal constant [3 x i8] c"%d\0a", align 1