\set ON_ERROR_STOP on

create extension if not exists vector;
drop schema if exists pgvector_skill_test cascade;
create schema pgvector_skill_test;
set search_path = pgvector_skill_test, public;

create table items (
  id bigint primary key,
  tenant_id integer not null,
  body text not null,
  embedding vector(3) not null
);

insert into items (id, tenant_id, body, embedding) values
  (1, 1, 'alpha', '[1,0,0]'),
  (2, 1, 'near alpha', '[0.9,0.1,0]'),
  (3, 1, 'middle', '[0.5,0.5,0]'),
  (4, 1, 'orthogonal', '[0,1,0]'),
  (5, 2, 'other tenant alpha', '[1,0,0]'),
  (6, 2, 'other tenant beta', '[0,1,0]'),
  (7, 2, 'other tenant gamma', '[0,0,1]'),
  (8, 2, 'other tenant mixed', '[0.3,0.3,0.4]');

create index items_tenant_idx on items (tenant_id);
create index items_embedding_hnsw_idx
on items using hnsw (embedding vector_cosine_ops);
analyze items;

begin;
set local enable_seqscan = off;
set local hnsw.ef_search = 100;

-- Prove the distance operator, ordering shape, and LIMIT are eligible for HNSW.
explain (analyze, buffers, format json)
select id
from items
order by embedding <=> '[1,0,0]'::vector
limit 3;

-- Keep filtering correctness separate from ANN-path eligibility. On this tiny
-- table PostgreSQL may reasonably prefer the tenant B-tree followed by a sort.
explain (analyze, buffers, format json)
select id
from items
where tenant_id = 1
order by embedding <=> '[1,0,0]'::vector
limit 3;

select array_agg(id order by distance) as nearest_ids
from (
  select id, embedding <=> '[1,0,0]'::vector as distance
  from items
  where tenant_id = 1
  order by embedding <=> '[1,0,0]'::vector
  limit 3
) ranked;

do $$
declare
  actual_ids bigint[];
begin
  select array_agg(id order by distance)
  into actual_ids
  from (
    select id, embedding <=> '[1,0,0]'::vector as distance
    from items
    where tenant_id = 1
    order by embedding <=> '[1,0,0]'::vector
    limit 3
  ) ranked;

  if actual_ids <> array[1, 2, 3]::bigint[] then
    raise exception 'unexpected nearest ids: %', actual_ids;
  end if;
end
$$;

commit;
drop schema pgvector_skill_test cascade;
