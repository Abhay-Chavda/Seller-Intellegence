CREATE TABLE IF NOT EXISTS user_foundry_agents (
    id SERIAL PRIMARY KEY,
    seller_id INTEGER NOT NULL REFERENCES users(id),
    agent_name VARCHAR(200) NOT NULL,
    agent_version VARCHAR(40) NOT NULL,
    model VARCHAR(120) NOT NULL,
    connection_id VARCHAR(500) NOT NULL,
    openapi_spec_url VARCHAR(500) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_user_foundry_agents_seller_id UNIQUE (seller_id)
);

CREATE INDEX IF NOT EXISTS ix_user_foundry_agents_seller_id ON user_foundry_agents (seller_id);
CREATE INDEX IF NOT EXISTS ix_user_foundry_agents_agent_name ON user_foundry_agents (agent_name);
