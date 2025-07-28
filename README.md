# BlockAssist

**NOTE: this README.md is geared towards testing. It will be buffed prior to release.**

BlockAssist is a distributed extension of the paper [AssistanceZero: Scalably Solving Assistance Games](https://arxiv.org/abs/2504.07091).

## Installation (Mac)

*You only need to ever run these once, you can skip when running future tests*
**Clone and enter repo**
```
git clone git@github.com:gensyn-ai/blockassist-private.git
cd blockassist-private
```

**Ensure pyenv installed**
```
brew update
brew install pyenv
```

**Set up logging directory**
```
mkdir -p logs
touch logs/malmo.log logs/yarn.log logs/blockassist.log
```


## Run execution scripts
Run each script in a separate terminal. If you ever want to know what a given script is doing: `tail -f logs/[execution_script].logs`. Leave all of these terminals running until told otherwise.

**Run Malmo (Minecraft)**
```
./scripts/run_malmo.sh
```

**Run Modal Login**
```
./scripts/yarn_run.sh
```
and login on your web browser at the address `localhost:3000`

**Set some env variables**

Note that this step is totally unoptimised.

```
export HF_TOKEN=[your_token]
export BA_ADDRESS_EOA=$(jq -r 'to_entries[0].value.address' modal-login/temp-data/userData.json)
export BA_ORG_ID=$(jq -r 'to_entries[0].value.orgId' modal-login/temp-data/userData.json)
```


**Run BlockAssist**

Note, before doing this open *another* terminal and `tail -f logs/blockassist.log`. This will allow you to monitor progress.

```
./scripts/run_blockassist.sh
```

**Play a few seconds of Minecraft**

Go to the minecraft window which is still showing (one will be minimised). Click the window. Press enter. Move around a bit. Press escape. Go back to the terminal window where you ran the above BlockAssist command and press `ctrl + c` once.

**Review logs**

If you reach this stage in the logging window, and can see a transactions in the block explorer then the test has worked.

Logging window:
```
[2025-07-28 05:03:48,955][blockassist.globals][INFO] - Successfully uploaded model to HuggingFace: h-grieve/blockassist-bc-bellowing_pouncing_horse_1753675374 with size 20.00 MB
```
[Block explorer](https://gensyn-testnet.explorer.alchemy.com/address/0xa6834217923D7A2A0539575CFc67abA209E6436F?tab=logs):
```
huggingFaceID
string
false
h-grieve/blockassist-bc-bellowing_pouncing_horse_1753675374
```

You should now `ctrl+c` and kill all the terminal windows


## Configuration

BlockAssist uses Hydra for configuration management. You can modify settings in the `config.yaml` file or override them via command line arguments.
`episode_count` - Controls number of episodes. If `episode_count`>1, a new episode will be started every time you `ctrl+c`
`num_training_iters` - Controls number of training iterations on all your recorded episodes

## Testing & Contributing

### Linting / Testing

This project relies mostly on ruff for formatting/linting purposes. To format, simply run:

    ruff check --select I --fix .

Pytest is used to run unit/integration tests. See below.

    pytest .


## Telemetry

This repository uploads telemetry to Gensyn services. To disable telemetry, export the following variable:

```bash
export DISABLE_TELEMETRY=1
```
