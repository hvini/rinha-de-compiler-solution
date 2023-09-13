; ModuleID = "module"
target triple = "x86_64-apple-darwin21.6.0"
target datalayout = "e-m:o-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"

declare i32 @"printf"(i8* %".1", ...)

define i32 @"main"()
{
entry:
  %"str" = alloca [12 x i8]
  store [12 x i8] c"Hello world\00", [12 x i8]* %"str"
  %".3" = getelementptr [3 x i8], [3 x i8]* @"format_string", i32 0, i32 0
  %".4" = call i32 (i8*, ...) @"printf"(i8* %".3", [12 x i8]* %"str")
  ret i32 0
}

@"format_string" = internal constant [3 x i8] c"%s\0a", align 1