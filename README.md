# SlackFS

SlackFS is a FUSE plugin which creates a virtual filesystem representing a Slack. Each channel is represented as a text file which contains a chronological message log.

SlackFS uses RethinkDB to aggregate Slack channel messages. As a result, it depends on a sister project, HookDB, which is a simple Webhook listener written in Flask. HookDB listens for Slack Wehbook messages and saves them to a RethinkDB instance, with each channel getting its own table.

```
./slackfs.py --mount=./test --db_host=lab.lbcpu.com --db_name=hookdb
```