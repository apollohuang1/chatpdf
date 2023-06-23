const {OpenAIEmbeddingFunction} = require('chromadb');
const { ChromaClient } = require("chromadb");
const client = new ChromaClient();
export default {
  async fetch(
    request: Request,
    ctx: ExecutionContext
  ): Promise<Response> {
    const embedder = new OpenAIEmbeddingFunction({openai_api_key: "<><><><>"})
    const collection = await client.createCollection({ name: "my_collection", embeddingFunction: embedder });
    await collection.add({
      ids: ["id1", "id2"],
      metadatas: [{ source: "my_source" }, { source: "my_source" }],
      documents: ["This is a document", "This is another document"],
    });
    const results = await collection.query({
      nResults: 2,
      queryTexts: ["This is a query document"],
    });

    // console.log("RESULTS:", results);

    return new Response("Hello world!", {
      headers: { "content-type": "text/plain" },
    });
  },
};
