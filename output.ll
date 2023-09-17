; ModuleID = "module"
target triple = "x86_64-apple-darwin21.6.0"
target datalayout = "e-m:o-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"

declare i32 @"printf"(i8* %".1", ...)

define i32 @"main"()
{
entry:
  %".2" = call i32 @"combination"(i32 10, i32 2)
  %".3" = getelementptr [4 x i8], [4 x i8]* @"format_Call", i32 0, i32 0
  %".4" = call i32 (i8*, ...) @"printf"(i8* %".3", i32 %".2")
  ret i32 0
}

define i32 @"combination"(i32 %".1", i32 %".2")
{
entry:
  %".4" = icmp eq i32 %".2", 0
  %".5" = icmp eq i32 %".2", %".1"
  %".6" = or i1 %".4", %".5"
  br i1 %".6", label %"entry.if", label %"entry.else"
entry.if:
  ret i32 1
entry.else:
  %".9" = sub i32 %".1", 1
  %".10" = sub i32 %".2", 1
  %".11" = call i32 @"combination"(i32 %".9", i32 %".10")
  %".12" = sub i32 %".1", 1
  %".13" = call i32 @"combination"(i32 %".12", i32 %".2")
  %".14" = add i32 %".11", %".13"
  ret i32 %".14"
entry.endif:
  ret i32 0
}

@"format_Call" = internal constant [4 x i8] c"%d\0a\00", align 1