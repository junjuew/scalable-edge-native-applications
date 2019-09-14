* mysql-bk: experiments database backup
* profile: a symlink to application profiles (e.g. utility vs resources given)
* sec5-resource-allocation: experiment configuration files (*.yml) and logs of the experiment. Evaluating the effect of resource allocation only on total system utilities. Presented in terms of frame-level latency and throughput.
* sec6-dutycycleimu: evaluate the effect of running dutycyle + imu suppression on client on resource utilization on the cloudlet. Presented as # of cores vs frame processed + # of cores vs active frames (frames that potentially trigger instructions) processed.
* sec6-instruction-latency: similar dir structure to sec5-resource-allocation. Evaluating the combined effects of resource allocation on the cloudlet + dutycycleimu at the client. Presented in terms of instruction latency.