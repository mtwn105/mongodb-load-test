# Upstream provenance

The following two files are unmodified copies from the original YCSB 0.17.0 tag, accessed 2026-10-24:

- src/main/java/site/ycsb/db/MongoDbClient.java — https://raw.githubusercontent.com/brianfrankcooper/YCSB/0.17.0/mongodb/src/main/java/site/ycsb/db/MongoDbClient.java
- src/main/java/site/ycsb/db/OptionsSupport.java — https://raw.githubusercontent.com/brianfrankcooper/YCSB/0.17.0/mongodb/src/main/java/site/ycsb/db/OptionsSupport.java

Their upstream copyright and Apache 2.0 notices are retained. YCSB-LICENSE.txt is copied from https://raw.githubusercontent.com/brianfrankcooper/YCSB/0.17.0/LICENSE.txt. SHA256SUMS records the exact source/license bytes.

Only the synchronous binding is compiled. The unused third-party asynchronous binding is omitted. Maven resolves YCSB core 0.17.0 and the original MongoDB Java driver 3.8.0. JAXB API 2.3.1 supplies DatatypeConverter needed by HDR export on the tested Java 21 runtime. This is a pinned historical YCSB client stack, not a claim of current production-driver support. The observed MongoDB 8.0.34 read/update compatibility is limited to this executed experiment.

DEPENDENCIES.sha256 records every resolved runtime JAR. Setup checks both manifests. Third-party dependencies retain their respective licenses; no license for the original lab scripts has been selected.
