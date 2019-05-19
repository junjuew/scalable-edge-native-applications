#/bin/bash -ex

# exp_cpus="1 0.8 0.6"

exp_cpus="0.2 0.4 0.6 0.8 1.0 1.2 1.4 1.6. 1.8 2.0"
for exp_cpu in ${exp_cpus};
do
    docker_name=rmexp-${exp_name};
    exp_name=sec6-res-util-lego-c${exp_cpu}m2
    ssh -t junjuew@cloudlet002.elijah.cs.cmu.edu "/bin/bash -l -c \" \
    docker stop -t 0 ${docker_name};
    sleep 5;
    cd /home/junjuew/work/resource-management;
    source .envrc
    ./serve-container.sh -a lego -e ${exp_name} -g rmexp -n 1 --docker-args --cpus=${exp_cpu} --memory=2g
    \""

    sleep 10;

    ssh -t root@n6  "sudo /bin/bash -l -c \" \
    cd /sdcard/resource-management;
    source .envrc
    unbuffer timeout 120 python rmexp/feed.py start_single_feed_token \
    --video-uri data/lego-trace/1/video.mp4 \
    --broker-uri tcp://128.2.210.252:9094 \
    --broker-type ${BROKER_TYPE} \
    --tokens-cap 2 \
    --app lego \
    --client_type device \
    --print-only True \
    --exp ${exp_name} > ${exp_name}.log \""

    sleep 10;
done

docker_name=rmexp-${exp_name};
EXP=sec6-res-util-lego-c${exp_cpu}m2
ssh -t junjuew@cloudlet002 "/bin/bash -l -c \" \
docker stop -t 0 ${docker_name};
\""