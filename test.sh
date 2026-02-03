for i in $(seq 1 500);
do
    python3 main.py "$(python3 bonus_shuffle.py 31)" --fast
done


# F L2 D2 F2 L B L2 F B' F U2 L2 B' L U' D' B' U L R' U D2 L' R2 L B2 R' F' R2 D2