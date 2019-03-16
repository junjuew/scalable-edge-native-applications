#! /bin/bash -ex

# get basic environ setup
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source ${DIR}/.envrc

echo "# of cpus"
read num_cpu
[[ -z "${num_cpu}" ]] && echo "# cpus cannot be empty" && exit

echo "# of memory"
read num_memory
[[ -z "${num_memory}" ]] && echo "# memory cannot be empty" && exit

read -r -p "Drop into Container Bash? [y/n] " interactive
if [[ "$interactive" =~ ^([yY][eE][sS]|[yY])+$ ]]
then
    # launch interactive container
    exec docker run -it --rm --name=rmexp --cpus=${num_cpu} --memory=${num_memory} res /bin/bash
else
    # get exp configuration
    echo "# of feeds"
    read num_feed
    [[ -z "${num_feed}" ]] && echo "# feed cannot be empty" && exit

    echo "fps:"
    read fps
    [[ -z "${fps}" ]] && echo "fps cannot be empty" && exit

    echo "# of worker processes:"
    read num_worker
    [[ -z "${num_worker}" ]] && echo "# worker cannot be empty" && exit

    read -r -p "experiment prefix (default: ${EXP_PREFIX}) " prefix
    prefix=${prefix:-$EXP_PREFIX}

    exp_name="p${prefix}f${num_feed}fps${fps}w${num_worker}c${num_cpu}m${num_memory}"
    echo "experiment name (default: ${exp_name}):"
    read custom_exp_name
    exp_name="${custom_exp_name:-$exp_name}"
    echo "experiment name: ${exp_name}"

    echo "launching redis server in a container (feeds-queue)..."
    docker stop -t 0 feeds-queue || true
    docker run --rm --name feeds-queue -p 127.0.0.1:6379:6379 -d redis
    
    # launch exp
    echo "launching experiment container (rmexp)"
    docker run --rm --name=rmexp --cpus=${num_cpu} --memory=${num_memory} --link feeds-queue:redis res /bin/bash -l -c \
    "conda activate resource-management && source .envrc && EXP=${exp_name} OMP_NUM_THREADS=4 python rmexp/serve.py start --num ${num_worker} --host redis --port 6379"
fi