const app = express();
app.get('/u', async (req, res) => {
  const r = await db.query(`SELECT * FROM users WHERE id = ${req.query.id}`);
  const safe = await db.query('SELECT * FROM users WHERE id = $1', [req.query.id]);
  const u = await User.findOne(req.body);
  await prisma.user.create({ data: req.body });
  await prisma.$queryRawUnsafe(q);
  exec(`convert ${req.query.f}`);
  res.sendFile(path.join(__dirname, req.params.name));
  const page = await axios.get(req.query.url);
  res.redirect(req.query.next);
  res.send(`<h1>${req.query.q}</h1>`);
  const token = Math.random().toString(36) + 'token';
});
app.use(cors({ origin: true, credentials: true }));
