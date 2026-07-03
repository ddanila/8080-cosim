# Emaplaat position harvest (7.102.100 assembly drawing, emaplaat-1.png)
Calibration: board outline left x=1260px, top y=749px, right x=4930px, bottom y=3811px
=> x_mm = (px-1260)/11.84 ; y_mm = (px-749)/11.51  (scales verified: DIP-24 ROM width
reads 15.2mm; board#2 photo DRAM field 115-197mm matches; bl_q D91 row cross-checks)
Rot convention (ours): 0 = vertical (long axis N-S, notch up), 90 = horizontal.

## DRAM array (from dramrow1 + bl_q, high confidence)
columns x = 119.6 + 11.24*k, k=0..7 ; rows y = 151.9 + 26.2*r, r=0..3 ; all vertical (rot 0)
row1: D67 D66 D65 D64 D63 D62 D61 D60 (left->right)
row2: D75 .. D68 ; row3: D83 .. D76 ; row4: D91 .. D84
decap channel caps between row1/row2: C36 C55 C40 C59 C44 C63 C48 C67 (y~166)
between row2/row3 (from bl_q area): C37 C56 C41 C60 C45 C64 C49 C68 (y~218?) CHECK
R52 right of row1 x~200 y~152v ; R55 x~200 y~178v ; R51 x~200 y~230v? ; R58? 

## clock/video band y 150-190 (dramrow1, high confidence)
D38 (233.4, 161.8) v    # КР531ЛА1
D92 (260.0, 164.5) v    # ЛЕ4 (decapped on board2)
D39 (284.3, 161.3) v
D34 (297.5, 163.0) v    # ЛП5
D36 (228.1, 186.4) v
D37 (241.7, 187.0) v
D33 (258.0, 186.0) v
D103 (274.2, 187.8) v   # ИЕ10
D56 (287.8, 186.0) v    # АГ3
R46+C6 between (250-262, ~173) h pair ; R35 v (222,158)? ; C29+C104 v pair (~218,166)
C89 v (~215,155)? ; mounting hole ~ (300,152)
wire posts: 10 at x~120 y~152ch, 13 at x~228 y~157, 9 at x~112 y~178->(233,172)

## lower-left CPU cluster (ema_leftedge, offsets: tile (1100,1800))
D5  (27, 117) h   # 8238; spans x12-42
D6  (~62, 117) h  # right of D5; D8? follows
D4  (44.5, 147) v
D2  (83.2, 147) v
D1  big chip below-left (partial, ~x20-30, y>150) CHECK tile3
R13 h (~52,103); posts 8 (x~40,y103) 19 (x~48,y131); R11/R14 pair (~78,131)
R12 (~58,152) h; mounting hole (9.7, 150.8)
resistor pack col (x~103-113, y95-112): R28? R27? R26? R25? (4x v)

## bottom-left band (ema_bl_q, tile offset (0,3139))
D13 (30?, 211) h  # display(1090,25)->orig(1635,3176)-> (31.7, 210.9) h
D105 (31.7, ~222) h  # below D13, R1+C91 between
D52 (60.6, 237.5) v  # К555КП14! NOT (234,224.5)
C24 v (~74, 237)? ; C21? (~73,212)?
R43/R44/R45/R42 v cluster (x~91-98, y~230-240)
D47 (79.2, 232) v ; D45 (91.7, 232) v ; D49 (103.9, 229.2) v  # CHECK vs D46/D44/D48 row above
E4 (44-47, 250-253) ; E5 (50-53, 250) ; E2/E3 (56-60, 248-252)  # jumper posts!
VD5 diode (~62,238)? ; R19 h (~59,222)
C31 C32 C33 electrolytic stack vertical x~24, y~235-252
C1 (~29,205) big v ; R1+C91 (~30,216) ; R4/R2/VD1 (24-27, 225-232)
C92 (~34,232) ; C93+C33? ; C73 disc (64.5->?) (~64,240)? Z=Z1 area (75-83, 237-247)
X8 pads 62 61 60 59 at x~52-63, y~253-257; X8 shell below board edge
mounting hole (12.5, 235)?; D59 (~105,242+) h CHECK ; D42 (~120,242) h CHECK
DRAM row4 D91 (119.6, 230.5) leftward-confirmed; E1 post (~113,230)
E13 post (~104,218)?

## top strip (t1, offset (1260,749), factor 1.12)
X1 body x 13.2-107.4, base y 21.9-33.6; mount holes (10.2,27.9) + (114.4,28.7)
X2 body x 117.8-168.9 same y band
conn #21 (X4?) from x 171.7 cut right ->t2
D25 (29.8, 55.2) h ; C74 (40.2, 55.5) v
D23 (54.6, 55.2) h ; C75 (94.6, 55.5) v
D24 (81.6, 55.2) h
D29 (108.5, 55.2) h ; C76 (124.9, 55.5) v
D27 (152.0, 51.0) h BIG DIP-40 ; C78 (178.3, 55.8) v
D104 (184.9, 55.0) v ; R48 h (179, 38.6)
ROM row D15..D22 vertical, centers x = 22.9, 42.3, 62.9, 82.6, 102.6, 122.5, 142.6, 162.5
  (pitch ~20), y center ~79 (row spans ~63-95)
E7 jumper (5.2, 87) ; E6 jumper (177.4, 88.7)
C90 (9.9, 66.9) v ; C77 (185, 70.5) v
D11 at right edge x>=178 cut -> t2

## tile2 top-right (offset (3500,749), 1:1 display): x_mm = dx/11.84+189.2 ; y_mm = dy/11.51
FDC QUADRANT (D28,D93-D102,D106,D94-100): emaplaat layout DIFFERS from real board -- owner
warned; KEEP owner/photo placements. Emaplaat values recorded for reference only:
  D32 (198.9,43.0)v ; D14 (198.9,53.6)v ; D28* (214.5,49.3)v ; D97* (229.3,50.4)v
  D95* (244.3,51.7)v ; D94* (258.9,51.7)v ; D98* (274.2,52.1)v ; D96* (~289,52)v
  D93* (233.4,83.9)v ; D102* (~251,76)v ; D101* (267.3,76.5)v ; D99* (282.5,76.5)v
  D100* (296.9,76.0)v ; D106* (289.3,100.3)v
NON-quadrant finds (APPLY):
  D32 (198.9,43.0) v  # АП2 #2
  D14 (198.9,53.6) v  # АП2 #1
  D12 (206.5,77.5) v  # ЛА18
  D3  (206.9,94.5) v  # К561ЛН2
  XL1 (240.3,121.4)   # FDC crystal + C12 (255.5,115.6) disc, C15 (253.2,123.4)
  VT4 (265.2,115.1) transistor; VT2 (~273,~139); VD3 (~294,~130)
  C22 (272.4,36.9) h ; big electrolytic C34? (278.7,34.3) v
  C16 (266.9,89.9) h ; C17 (266.9,99.9) h ; C79 (300.7,~52) v
  R30 h (~208,64.3); R16 h (~208,105.6); R10/R9 (~198,101); R15 (~213,87.5); R102 (~199,77)
  bracket connectors: X3(k3) x~190, X4(k4) x~220, X5 x~245, X7(BNC) x~266, X6 x~295 (top edge)
  posts: E10 + R100 (~236,36.5); "5"/"6" posts (~242,105); "8" post (~235,108); "20" (~200,94)
  D41 D40 labels at tile bottom edge y~140+ -> tile4

## tile3 mid-left (offset (1260,1900), 1:1): x=dx/11.84, y=(dy+1151)/11.51 -- APPLY ALL
D5  (31.2,117.9) h DIP-28 ; C87 v (51.5,123)
D6  (63.8,121.4) h ; C88? v (76.2,123)
D8  (88.3,121.4) h
D9  (~113,121.4) h (right edge cut; refine t3b)
D1  (32.3,162.1) v DIP-40 (51.3mm long ok)
D4  (51.1,147.1) v DIP-20
D107 (51.1,173.8) v DIP-20  # below D4, confirms audit fix; refine from (57,185)
D2  (78.7,147.2) v (socketed)
D50 (106.2,152.1) v ; D51 (106.2,178.9) v  # row muxes, align DRAM rows 1-2
R-pack 8x (79.4-98.4, 104-112) = R21..R28 pull-ups ; R13 h (56,108.3)
R11/R14 stacked h (67.4,131.7/133.3) ; R7 h (96.3,128.7) ; R17or47 v (111.1,134.6)
R18 v (15,160.4) ; R12 h (71.2,166.6) ; R29 v (44.8,185.8) ; R37/R36 v (15.6/19.6,182.5)
C99 h (105,161.9) ; C95 h (105.8,165.2) ; R50 v (112.3,172.9)
E11/E12 jumper block posts (94-96,169-186)
mounting hole (10.1,150.5) ; posts: 8(44.8,107.5) 19(38.4,130.4) 14(23.2,190.5)
  10(112.3,159.1) 13(96.3,162.6) 9(111.9,185.6)

## tile3b D7/D10 strip (offset (2550,2050)): APPLY
D9  (113.2,121.9) h ; C10? v (122.3,121.5)
D7  (137.2,121.9) h
D10 (178.9,120.6) h DIP-28
post 11 (148.2,131.3)
decap row ABOVE DRAM row1 y=139.3: C35(119.7) C54(130.9) C39(142.3) C58(153.7)
  C43(164.7) C62(176.1) C47(187.1) C..(198?) -- x == DRAM columns

## tile4 bottom-right (offset (2700,2950), f=1.11): APPLY
DRAM row3 y=205.4 (D83..D76), row4 y=229.6 (D91..D84) refdes CONFIRMED
cap row3/4: C57 C42 C61 C46 C65 C50 C69 (+C34/C37... left) y=216.8
D53 (227.8,211.7) v   # КР531ИД7 RAS/CAS -- was (253,225)
D35 (245.1,210.8) v   # К155ЛН5 -- move
D57 (274.9,213.4) h DIP-24  # ВИ53 #1
D55 (274.9,236.8) h   # ВИ53 #2
D54 (274.7,259.3) h   # ВИ53 #3
D26 (232.0,259.3) h DIP-40  # ВВ55А #1
E3 posts (217,235.5) ; E2 posts (217,242.5)  # my bl_q "E2/E3 at x~56" was a MISREAD -- drop it
R39 (235.0,206.6) v ; C96 (227.9,199.1) h ; R60 (252,223.4) h
wire posts: 2 (250.9,219.9), 1 (250.4,227.6), 14+7 (251,195.5), 12 (241.2,199.9)
VT1 (251,238.2) + R90/R91 + VD4 (251.5,246) + R48 (244.9,229.8) h  # reset/beep cluster
  (tile1's "R48(179,38.6)" was actually R104 -- correct that entry)
C98 (182.6,262.8) h ; R54 (204.1,197.2) v ; R5x (204.1,209.6) v ; R53 (204.1,222.9) v
R49 (204.1,235.1) v
D41/D40 h chips at y~140-148 x 225-260 (cut) -> tile5

## tile5 (offset (3400,2150)): APPLY
D41 (235.0,145.6) h  # ИР16 -- was (255,155,270)
D40 (258.0,145.6) h  # ИЕ17 -- move
R56 (204.8,146) v ; C8x v (246,146.3) between D41/D40 ; R4x v (271.2,148.5)
post 11 RIGHT end (262.2,132.6)  # wire 11 spans (148.2,131.3)<->(262.2,132.6)
FDC analog cluster: R65(277.9,135.3) C94(284.2,140.1) VT2(280.4,146.5) R33(280.4,149.9)
  posts 3(280.4,134.9) 4(284.6,131.7) ; R7x cluster (289,135-152) ; VD3 (~291,133)
mid-right mounting hole (300.3,153.0)
C47 col7 / C66 col8 confirm cap-row-above-row1 y=140

## RECALIBRATION (right-side profile view): BOARD = 310 x 279 mm (dim "279*"); tech notes:
element grid = 2.5mm (ОСТ4 ГО.010.030), R1..R106, C1..C97+, D1..D108 ranges exist.
Bottom edge = 4066px -> y-scale 11.89 px/mm (square-ish with x 11.84). ALL tile y values
computed with /11.51 must be multiplied by 0.968.

## FINAL APPLY TABLE (netted chips; x, y in mm; h=rot90, v=rot0)
D1 (32.3,157)v D2 (78.7,142.5)v D4 (51.1,142.4)v D107 (51.1,168.2)v D5 (31.2,114.1)h
D6 (63.8,117.5)h D8 (88.3,117.5)h D9 (113.2,118)h D7 (137.2,118)h D10 (178.9,116.7)h
D11 (188,80.8)v D12 (206.3,74)v D3 (205.8,89.5)v D14 (198.9,51.9)v D32 (198.9,41.6)v
D13 (31.9,205.3)h D105 (31.9,219.8)h D30 (32.9,191.5)h S1[=S3 label] (63.5,197.9)
D52 (58.3,221.5)v D46 (80.7,198.5)v D44 (93.3,198.5)v D48 (105.6,198.5)v
D47 (80.7,223)v D45 (93.3,223)v D49 (105.6,223)v
D50 (106.2,148)v D51 (106.2,173)v
DRAM cols x=119.6 130.9 142.3 153.7 164.7 176.1 187.1 198.4 ; rows y=148 173 198 223
D53 (227.8,204.9)v D35 (245.1,204.1)v D38 (233.4,156.6)v D92 (260,159.2)v D39 (284.3,156.1)v
D34 (297.5,157.8)v D36 (228.1,180.4)v D37 (241.7,181)v D33 (258,180)v D103 (274.2,181.8)v
D56 (287.8,180)v D40 (258,140.9)h D41 (235,140.9)h
D57 (274.9,206.6)h D55 (274.9,229.2)h D54 (274.7,251)h D26 (232,251)h
D42 (136,259)h D43 (159.6,259.5)h D58 (183,259.5)h D59 (106.6,257)h
D25 (29.8,53.4)h D23 (54.6,53.4)h D24 (81.6,53.4)h D29 (108.5,53.4)h D27 (152,49.4)h
D104 (184.9,53.2)v ROM D15..D22 x=22.9 42.3 62.9 82.6 102.6 122.5 142.6 162.5 y=76.5 v
E2 (217.5,235) E3 (217.5,227.5) jumpers
Z1 (79.4,258) C73 (58,256) C31 (23,242.5)h C32 (23,249.5)h C33 (24.5,258.5)h
C1 (18.4,209.5)v C21 (51.7,220.5)v R3 (12,215.4)v R4 (16.9,223.8)h R19 (44.4,235.3)h
R20 (51.9,208.9)v R38 (121.4,263.5)h R39 (235,201.6)v VD5 (49.4,246)h
X8 at (24,267) pads 62/61/60/59 left->right ; X9-like conn mount (208.6,271)
mount holes: (10.1,145.7) (104,265.8) (199,265.6) (300.3,148.1) + X1 corner pair
wire posts (sel): 12L(47.7,200.4) 11(148.2,127.1)<->(262.2,128.4) 2(99.2,223.5)<->(250.9,212.6)
  3(98.4,213.4)<->(280.4,130.6) 4(98.4,206.4)<->(284.6,127.5) 7/14(251,189.2) 20(199,90.8)
FDC quadrant (owner truth, unchanged): D93 D94 D100 D98 D106 D28 D96 D95 D97 D101 D99 D102
notch pass pending: ROM row notch-DOWN, DRAM notch-UP per drawing
