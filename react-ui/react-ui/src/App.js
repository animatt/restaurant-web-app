import React, { Component } from 'react';
import {BrowserRouter as Router, Route} from 'react-router-dom';
import './App.css';

import Navbar from './navbar/Navbar';
import Content from './content/Content';

class App extends Component {
	render() {
		return (
			<Router>
			  <div className="App">
				<Navbar />
				<Content />
			  </div>
			</Router>
		);
	}
}

export default App;
