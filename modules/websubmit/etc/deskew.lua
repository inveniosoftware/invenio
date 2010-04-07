-- FIXME this should do the right thing for grayscale images:
-- threshold, compute rotation, then rotate the grayscale image

if #arg < 2 then
    print("usage: ... input output")
    os.exit(1)
end

proc = ocr.make_DeskewPageByRAST()

input = bytearray:new()
output = bytearray:new()
iulib.read_image_gray(input,arg[1])
proc:cleanup(output,input)
iulib.write_image_gray(arg[2],output)
