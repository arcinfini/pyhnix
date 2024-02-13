
ALTER TABLE team RENAME COLUMN guildid TO guild_id;
ALTER TABLE team RENAME COLUMN lead_roleid TO lead_role_id;
ALTER TABLE team RENAME COLUMN member_roleid TO member_role_id;

ALTER TABLE team_member RENAME COLUMN teamid TO team_id;
ALTER TABLE team_member RENAME COLUMN userid TO user_id;