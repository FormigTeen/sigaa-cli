const { Sigaa } = require('sigaa-api');

// Parâmetros de login
const  PARAMS = {
  url: 'https://sigaa.ufba.br',
  institution: 'UFBA',
  username: '',
  password: ''
}

const sigaa = new Sigaa({
  url: PARAMS.url,
  institution: PARAMS.institution
});

const main = async () => {
  const account = await sigaa.login(PARAMS.username, PARAMS.password); // login

  console.log('> Nome: ' + (await account.getName()));
  console.log('> Email: ' + (await account.getEmails()).find(Boolean));
  console.log('> Url foto: ' + (await account.getProfilePictureURL()));

  // Encerra a sessão
  await account.logoff();
};

main().catch((err) => {
  if (err) console.log(err);
});
