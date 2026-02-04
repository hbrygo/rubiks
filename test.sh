for i in $(seq 1 100);
do
    python3 main.py "$(python3 bonus_shuffle.py 21)" --fast
done
