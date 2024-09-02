
ALTER TABLE team_member DROP CONSTRAINT team_member_pkey;
ALTER TABLE team_member ADD CONSTRAINT team_member_pkey PRIMARY KEY (team_id, user_id);